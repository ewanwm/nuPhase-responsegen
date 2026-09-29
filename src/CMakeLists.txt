cmake_minimum_required(VERSION 3.31)

find_package(Python COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG)
find_package(NEUT)
find_package(ROOT)

pybind11_add_module(neut MODULE neutrw-binding.cpp)

target_link_libraries(neut PUBLIC NEUT::All ROOT::Core ROOT::Physics ROOT::Tree)
target_include_directories(neut PRIVATE ${NEUT_INCLUDE_DIR})
