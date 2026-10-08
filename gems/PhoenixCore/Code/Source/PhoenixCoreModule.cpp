#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixCoreModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixCoreModule, "{00000000-0000-0000-0000-b66c04936d49}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixCoreModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixCoreModule, Phoenix::PhoenixCoreModule)
}
