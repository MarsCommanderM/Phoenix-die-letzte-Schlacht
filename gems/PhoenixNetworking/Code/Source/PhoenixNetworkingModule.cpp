#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixNetworkingModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixNetworkingModule, "{00000000-0000-0000-0000-f73663da9104}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixNetworkingModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixNetworkingModule, Phoenix::PhoenixNetworkingModule)
}
