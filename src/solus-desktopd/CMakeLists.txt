cmake_minimum_required(VERSION 3.20)
project(solus-desktopd
    VERSION 1.0.0
    DESCRIPTION "Solus Desktop Customization Daemon"
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
    org.solus.Desktop.xml
)

# ------------------------------------------------------------------
# The solus-desktopd executable
# ------------------------------------------------------------------
add_executable(solus-desktopd ${SOURCES} ${HEADERS})

target_link_libraries(solus-desktopd PRIVATE
    Qt6::Core
    Qt6::DBus
)

target_include_directories(solus-desktopd PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Generate D-Bus adaptor from introspection XML
qt_add_dbus_adaptor(solus-desktopd
    ${CMAKE_CURRENT_SOURCE_DIR}/org.solus.Desktop.xml
    desktopd.h
    DesktopDaemon
)

# ------------------------------------------------------------------
# Installation
# ------------------------------------------------------------------
install(TARGETS solus-desktopd
    RUNTIME DESTINATION /usr/bin
)

# Install D-Bus service file for auto-activation
install(FILES org.solus.Desktop.xml
    DESTINATION /usr/share/dbus-1/interfaces
)

# Install systemd service unit
install(FILES ${CMAKE_SOURCE_DIR}/../systemd/solus-desktopd.service
    DESTINATION /usr/lib/systemd/system
)
