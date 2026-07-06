#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QIcon>
#include <QQuickStyle>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setApplicationName("Solus Control Center");
    app.setApplicationDisplayName("Solus Control Center");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("Solus Project");
    app.setOrganizationDomain("getsolus.io");
    app.setWindowIcon(QIcon::fromTheme("solus-control-center"));

    QQuickStyle::setStyle("Material");

    QQmlApplicationEngine engine;

    // Expose D-Bus interfaces to QML
    QDBusInterface *desktopInterface = new QDBusInterface(
        "org.solus.Desktop", "/org/solus/Desktop",
        "org.solus.Desktop", QDBusConnection::sessionBus(), &engine);

    QDBusInterface *hardwareInterface = new QDBusInterface(
        "org.solus.Hardware", "/org/solus/Hardware",
        "org.solus.Hardware", QDBusConnection::systemBus(), &engine);

    QDBusInterface *softwareInterface = new QDBusInterface(
        "org.solus.SoftwareCenter", "/org/solus/SoftwareCenter",
        "org.solus.SoftwareCenter", QDBusConnection::sessionBus(), &engine);

    engine.rootContext()->setContextProperty("DesktopDBus", desktopInterface);
    engine.rootContext()->setContextProperty("HardwareDBus", hardwareInterface);
    engine.rootContext()->setContextProperty("SoftwareDBus", softwareInterface);

    const QUrl url(QStringLiteral("qrc:/qml/Main.qml"));
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreationFailed,
        &app, []() { QCoreApplication::exit(-1); });

    engine.load(url);

    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}