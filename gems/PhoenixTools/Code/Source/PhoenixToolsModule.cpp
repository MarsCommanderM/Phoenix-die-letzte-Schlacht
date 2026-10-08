#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixToolsModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixToolsModule, "{00000000-0000-0000-0000-28c5b6c06c5e}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixToolsModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixToolsModule, Phoenix::PhoenixToolsModule)
}
