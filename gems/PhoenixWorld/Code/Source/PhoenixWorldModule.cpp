#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixWorldModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixWorldModule, "{00000000-0000-0000-0000-c86be7e7aac7}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixWorldModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixWorldModule, Phoenix::PhoenixWorldModule)
}
