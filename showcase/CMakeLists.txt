if (NOT TARGET imgui)
    add_subdirectory("${PROJECT_SOURCE_DIR}/examples/external" "${CMAKE_BINARY_DIR}/showcase-imgui")
endif ()
add_executable(threepp_showcase main.cpp)
target_link_libraries(threepp_showcase PRIVATE threepp imgui::imgui)
add_executable(timber_run timber_run.cpp)
target_link_libraries(timber_run PRIVATE threepp imgui::imgui)
add_executable(timber_rally rally.cpp)
target_link_libraries(timber_rally PRIVATE threepp imgui::imgui)

# A separate physical off-road bench. Existing rally controllers are preserved.
include(FetchContent)
FetchContent_Declare(playground_bullet
    URL https://codeload.github.com/bulletphysics/bullet3/tar.gz/refs/tags/3.25
    URL_HASH SHA256=c45afb6399e3f68036ddb641c6bf6f552bf332d5ab6be62f7e6c54eda05ceb77
    SOURCE_SUBDIR unused-playground-only
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
FetchContent_MakeAvailable(playground_bullet)
# Only the three CPU libraries; no upstream demos, OpenCL, Python or GPU physics.
set(BULLET_PHYSICS_SOURCE_DIR "${playground_bullet_SOURCE_DIR}")
set(BULLET_VERSION 3.25)
set(BUILD_SHARED_LIBS OFF)
foreach(lib LinearMath BulletCollision BulletDynamics)
    add_subdirectory("${playground_bullet_SOURCE_DIR}/src/${lib}" "${playground_bullet_BINARY_DIR}/${lib}" EXCLUDE_FROM_ALL)
    target_include_directories(${lib} PUBLIC "${playground_bullet_SOURCE_DIR}/src")
endforeach()
add_executable(suspension_playground suspension_playground.cpp)
target_link_libraries(suspension_playground PRIVATE threepp imgui::imgui BulletDynamics BulletCollision LinearMath)
add_custom_command(TARGET suspension_playground POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:suspension_playground>/playground-assets"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/safari-body.glb" "${CMAKE_CURRENT_SOURCE_DIR}/assets/baja-427.glb"
        "$<TARGET_FILE_DIR:suspension_playground>/playground-assets"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${PROJECT_SOURCE_DIR}/asset-library/materials/gravel-road/basecolor_1k.jpg" "$<TARGET_FILE_DIR:suspension_playground>/playground-assets/gravel-basecolor.jpg"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${PROJECT_SOURCE_DIR}/asset-library/materials/gravel-road/normal_gl_1k.jpg" "$<TARGET_FILE_DIR:suspension_playground>/playground-assets/gravel-normal.jpg"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${PROJECT_SOURCE_DIR}/asset-library/materials/gravel-road/roughness_1k.jpg" "$<TARGET_FILE_DIR:suspension_playground>/playground-assets/gravel-roughness.jpg"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${playground_bullet_SOURCE_DIR}/LICENSE.txt" "$<TARGET_FILE_DIR:suspension_playground>/playground-assets/BULLET-LICENSE.txt")
add_executable(baja427_preview baja427_preview.cpp)
target_link_libraries(baja427_preview PRIVATE threepp imgui::imgui)
add_custom_command(TARGET baja427_preview POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:baja427_preview>/baja427-assets"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/assets/baja-427.glb" "$<TARGET_FILE_DIR:baja427_preview>/baja427-assets/baja-427.glb")
add_executable(safari_ao_bake safari_ao_bake.cpp)
target_link_libraries(safari_ao_bake PRIVATE threepp)
target_include_directories(safari_ao_bake PRIVATE "${PROJECT_SOURCE_DIR}/src/external/nlohmann")
if (WIN32)
    target_link_libraries(safari_ao_bake PRIVATE bcrypt psapi)
endif ()
if (THREEPP_BUILD_TESTS)
    add_executable(RallyVehicle_test rally_vehicle_test.cpp)
    target_link_libraries(RallyVehicle_test PRIVATE threepp)
    add_executable(safari_dynamics_probe safari_dynamics_probe.cpp)
    target_link_libraries(safari_dynamics_probe PRIVATE threepp)
endif ()
add_custom_command(TARGET timber_rally POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/assets" "$<TARGET_FILE_DIR:timber_rally>/rally-assets"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${PROJECT_SOURCE_DIR}/asset-library" "$<TARGET_FILE_DIR:timber_rally>/rally-assets/library")
