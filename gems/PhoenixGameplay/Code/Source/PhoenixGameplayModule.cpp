#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixGameplayModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixGameplayModule, "{00000000-0000-0000-0000-bd3ba04db38b}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixGameplayModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixGameplayModule, Phoenix::PhoenixGameplayModule)
}
