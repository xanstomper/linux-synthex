cmake_minimum_required(VERSION 3.20)
project(synthex-desktopd
    VERSION 1.0.0
    DESCRIPTION "Synthex Desktop Customization Daemon"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------
find_package(Qt6 REQUIRED COMPONENTS Core DBus)

# ------------------------------------------------------------------
# Sources
# ------------------------------------------------------------------
set(SOURCES
    main.cpp
    desktopd.cpp
)

set(HEADERS
    desktopd.h
)

set(DBUS_XML
    org.synthex.Desktop.xml
)

# ------------------------------------------------------------------
# The synthex-desktopd executable
# ------------------------------------------------------------------
add_executable(synthex-desktopd ${SOURCES} ${HEADERS})

target_link_libraries(synthex-desktopd PRIVATE
    Qt6::Core
    Qt6::DBus
)

target_include_directories(synthex-desktopd PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Generate D-Bus adaptor from introspection XML
qt_add_dbus_adaptor(synthex-desktopd
    ${CMAKE_CURRENT_SOURCE_DIR}/org.synthex.Desktop.xml
    desktopd.h
    DesktopDaemon
)

# ------------------------------------------------------------------
# Installation
# ------------------------------------------------------------------
install(TARGETS synthex-desktopd
    RUNTIME DESTINATION /usr/bin
)

# Install D-Bus service file for auto-activation
install(FILES org.synthex.Desktop.xml
    DESTINATION /usr/share/dbus-1/interfaces
)

# Install systemd service unit
install(FILES ${CMAKE_SOURCE_DIR}/../systemd/synthex-desktopd.service
    DESTINATION /usr/lib/systemd/system
)
