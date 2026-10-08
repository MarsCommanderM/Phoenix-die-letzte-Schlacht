#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixCharacterModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixCharacterModule, "{00000000-0000-0000-0000-6b938d10c118}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixCharacterModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixCharacterModule, Phoenix::PhoenixCharacterModule)
}
