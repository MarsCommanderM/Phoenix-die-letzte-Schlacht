# AutoComponent definitions.
#
# O3DE Multiplayer compiles these XML files into C++ components and
# controllers. The generated *.AutoComponent.h/.cpp and AutoComponentTypes.*
# are build products and are never committed or hand-edited.
#
# This list holds ONLY generated-file inputs. Manual sources live in
# phoenix_{api,private,shared}_files.cmake and gem activation lives in
# enabled_gems.cmake; the three responsibilities stay separate.

set(PHOENIX_AUTOGEN_FILES
    Source/AutoGen/PhoenixNetworkPlayerComponent.AutoComponent.xml
    Source/AutoGen/PhoenixNetworkCharacterComponent.AutoComponent.xml
    Source/AutoGen/PhoenixNetworkGameplayComponent.AutoComponent.xml
    Source/AutoGen/PhoenixNetworkObjectiveComponent.AutoComponent.xml
    Source/AutoGen/PhoenixNetworkWorldComponent.AutoComponent.xml
)
