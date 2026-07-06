cmake_minimum_required(VERSION 3.20)
project(solus-control-center VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS
    Quick
    QuickControls2
    DBus
)

# QML resource files
qt_add_executable(solus-control-center
    main.cpp
    resources.qrc
)

target_link_libraries(solus-control-center PRIVATE
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::DBus
)

target_include_directories(solus-control-center PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Install
install(TARGETS solus-control-center RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY ui/ DESTINATION ${CMAKE_INSTALL_DATADIR}/solus-control-center/ui)
