cmake_minimum_required(VERSION 3.31)
project(nuPhase-responsegen VERSION 0.0)

find_package(Python COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG)
find_package(NEUT)
find_package(ROOT)

add_subdirectory(src)