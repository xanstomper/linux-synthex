cmake_minimum_required(VERSION 3.20)
project(solus-stored
    VERSION 1.0.0
    DESCRIPTION "Solus Software Center Daemon"
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
# The solus-stored executable
# ------------------------------------------------------------------
add_executable(solus-stored ${SOURCES})

target_link_libraries(solus-stored PRIVATE
    Qt6::Core
    Qt6::DBus
)

target_include_directories(solus-stored PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Generate D-Bus adaptor from introspection XML
qt_add_dbus_adaptor(solus-stored
    ${CMAKE_CURRENT_SOURCE_DIR}/org.solus.SoftwareCenter.xml
)

# ------------------------------------------------------------------
# Installation
# ------------------------------------------------------------------
install(TARGETS solus-stored
    RUNTIME DESTINATION /usr/bin
)

install(FILES org.solus.SoftwareCenter.xml
    DESTINATION /usr/share/dbus-1/interfaces
)

install(FILES ${CMAKE_SOURCE_DIR}/../systemd/solus-stored.service
    DESTINATION /usr/lib/systemd/system
)
