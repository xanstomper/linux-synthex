cmake_minimum_required(VERSION 3.20)
project(synthex-stored
    VERSION 1.0.0
    DESCRIPTION "Synthex Software Center Daemon"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------
find_package(Qt6 REQUIRED COMPONENTS Core DBus)

# ------------------------------------------------------------------
# Sources
# ------------------------------------------------------------------
set(SOURCES
    main.cpp
)

# ------------------------------------------------------------------
# The synthex-stored executable
# ------------------------------------------------------------------
add_executable(synthex-stored ${SOURCES})

target_link_libraries(synthex-stored PRIVATE
    Qt6::Core
    Qt6::DBus
)

target_include_directories(synthex-stored PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Generate D-Bus adaptor from introspection XML
qt_add_dbus_adaptor(synthex-stored
    ${CMAKE_CURRENT_SOURCE_DIR}/org.synthex.SoftwareCenter.xml
)

# ------------------------------------------------------------------
# Installation
# ------------------------------------------------------------------
install(TARGETS synthex-stored
    RUNTIME DESTINATION /usr/bin
)

install(FILES org.synthex.SoftwareCenter.xml
    DESTINATION /usr/share/dbus-1/interfaces
)

install(FILES ${CMAKE_SOURCE_DIR}/../systemd/synthex-stored.service
    DESTINATION /usr/lib/systemd/system
)
