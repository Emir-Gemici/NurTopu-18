# Navitas — Gazebo animasyon plugin'i derleme
cmake_minimum_required(VERSION 3.10)
project(navitas_plugins)

find_package(gazebo REQUIRED)

include_directories(${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})
list(APPEND CMAKE_CXX_FLAGS "${GAZEBO_CXX_FLAGS}")
set(CMAKE_CXX_STANDARD 17)

add_library(navitas_anim SHARED navitas_anim.cc)
target_link_libraries(navitas_anim ${GAZEBO_LIBRARIES})

# İHA tarama kamerası — kare+poz senkron kayıt (sensor plugin)
add_library(navitas_scan_cam SHARED navitas_scan_cam.cc)
target_link_libraries(navitas_scan_cam ${GAZEBO_LIBRARIES} CameraPlugin)
