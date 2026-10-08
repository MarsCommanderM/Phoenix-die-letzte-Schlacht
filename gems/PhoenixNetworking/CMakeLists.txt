cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixNetworking)

set(FILES
    Code/Source/Networking/PhoenixNetworkRegistration.cpp
    Code/Source/PhoenixNetworkingModule.cpp
    Code/Source/PhoenixNetworkingSystemComponent.cpp
    Code/Include/Phoenix/Networking/PhoenixNetworkPolicy.h
    Code/Include/Phoenix/Networking/PhoenixNetworkRegistration.h
    Code/Include/Phoenix/Networking/PhoenixNetworkingSystemComponent.h
    Code/Include/Phoenix/PhoenixNetworking/PhoenixNetworking.h
)
