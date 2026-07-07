#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QIcon>
#include <QQuickStyle>
#include <QProcess>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDir>
#include <QTimer>
#include <QDateTime>
#include <QRegularExpression>
#include <QDebug>

// Backend calls Synthex Rust tools and writes results to /var/run/synthex/*.json
class SynthexBackend : public QObject {
    Q_OBJECT
public:
    explicit SynthexBackend(QObject *parent = nullptr) : QObject(parent) {
        QDir().mkpath("/var/run/synthex");
        refreshAll();
        auto *timer = new QTimer(this);
        connect(timer, &QTimer::timeout, this, &SynthexBackend::refreshAll);
        timer->start(60000);
    }

public slots:
    void refreshAll() {
        runTool("synthex-recovery", {"--json", "diagnose"}, "recovery-status.json");
        runTool("synthex-service", {"--json", "summary"}, "service-status.json");
        runTool("synthex-kernel", {"--json", "current"}, "kernel-status.json");
        runTool("synthex-compat", {"scan"}, "compat-report.json");
        runTool("synthex-recovery", {"--json", "health"}, "system-health.json");
        captureSystemInfo();
    }

    QString runTool(const QString &tool, const QStringList &args, const QString &outputFile) {
        QProcess proc;
        proc.setProgram(tool);
        proc.setArguments(args);
        proc.setProcessChannelMode(QProcess::MergedChannels);
        proc.start();
        if (!proc.waitForFinished(30000)) {
            qWarning() << "Timeout:" << tool << args;
            return {};
        }
        QString out = QString::fromUtf8(proc.readAllStandardOutput());
        if (!outputFile.isEmpty() && !out.isEmpty()) {
            QFile f(QString("/var/run/synthex/%1").arg(outputFile));
            if (f.open(QIODevice::WriteOnly)) { f.write(out.toUtf8()); f.close(); }
        }
        return out;
    }

    void captureSystemInfo() {
        QJsonObject info;
        QFile cpu("/proc/cpuinfo");
        if (cpu.open(QIODevice::ReadOnly)) {
            for (auto &line : QString::fromUtf8(cpu.readAll()).split('\n'))
                if (line.startsWith("model name")) { info["cpu"] = line.section(':',1).trimmed(); break; }
            cpu.close();
        }
        QFile mem("/proc/meminfo");
        if (mem.open(QIODevice::ReadOnly)) {
            for (auto &line : QString::fromUtf8(mem.readAll()).split('\n'))
                if (line.startsWith("MemTotal")) { info["memory"] = line.section(':',1).trimmed(); break; }
            mem.close();
        }
        QProcess df;
        df.start("df", {"-h", "--output=size,used,avail,pcent", "/"});
        if (df.waitForFinished(5000)) {
            auto lines = QString::fromUtf8(df.readAllStandardOutput()).split('\n');
            if (lines.size() >= 2) {
                auto p = lines[1].split(QRegularExpression("\\s+"), Qt::SkipEmptyParts);
                if (p.size()>=4) { info["disk_size"]=p[0]; info["disk_used"]=p[1]; info["disk_avail"]=p[2]; info["disk_pct"]=p[3]; }
            }
        }
        info["timestamp"] = QDateTime::currentDateTime().toString(Qt::ISODate);
        QFile sf("/var/run/synthex/system-info.json");
        if (sf.open(QIODevice::WriteOnly)) { sf.write(QJsonDocument(info).toJson()); sf.close(); }
    }
};

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setApplicationName("Synthex Control Center");
    app.setApplicationDisplayName("Synthex Control Center");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("Synthex Project");
    app.setOrganizationDomain("getsynthex.io");
    app.setWindowIcon(QIcon::fromTheme("synthex-control-center"));

    QQuickStyle::setStyle("Material");

    QQmlApplicationEngine engine;

    // Expose D-Bus interfaces to QML
    QDBusInterface *desktopInterface = new QDBusInterface(
        "org.synthex.Desktop", "/org/synthex/Desktop",
        "org.synthex.Desktop", QDBusConnection::sessionBus(), &engine);

    QDBusInterface *hardwareInterface = new QDBusInterface(
        "org.synthex.Hardware", "/org/synthex/Hardware",
        "org.synthex.Hardware", QDBusConnection::systemBus(), &engine);

    QDBusInterface *softwareInterface = new QDBusInterface(
        "org.synthex.SoftwareCenter", "/org/synthex/SoftwareCenter",
        "org.synthex.SoftwareCenter", QDBusConnection::sessionBus(), &engine);

    engine.rootContext()->setContextProperty("DesktopDBus", desktopInterface);
    engine.rootContext()->setContextProperty("HardwareDBus", hardwareInterface);
    engine.rootContext()->setContextProperty("SoftwareDBus", softwareInterface);

    // Start the backend integration service
    SynthexBackend *backend = new SynthexBackend(&engine);
    engine.rootContext()->setContextProperty("SynthexBackend", backend);

    const QUrl url(QStringLiteral("qrc:/qml/Main.qml"));
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreationFailed,
        &app, []() { QCoreApplication::exit(-1); });

    engine.load(url);

    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}

#include "main.moc"