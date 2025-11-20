cmake_minimum_required(VERSION 3.10)
project(SafeBoxHost CXX)
set(CMAKE_CXX_STANDARD 17)

# Main library
add_library(safebox-lib src/host/safebox.cpp)
target_include_directories(safebox-lib PUBLIC src/host)

# Main executable
add_executable(safebox-host src/host/main.cpp)
target_link_libraries(safebox-host safebox-lib)

# Tests
enable_testing()
find_package(GTest QUIET)

if (GTest_FOUND)
    add_executable(safebox-host-tests tests/test_host.cpp)
    target_link_libraries(safebox-host-tests safebox-lib GTest::gtest GTest::gtest_main)
    add_test(NAME HostTests COMMAND safebox-host-tests)
else()
    message(WARNING "GTest not found. Skipping C++ tests. Install: sudo apt install libgtest-dev cmake")
endif()

install(TARGETS safebox-host DESTINATION bin)
