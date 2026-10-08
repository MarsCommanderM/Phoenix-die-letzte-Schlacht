#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixAIModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixAIModule, "{00000000-0000-0000-0000-93d172356d65}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixAIModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixAIModule, Phoenix::PhoenixAIModule)
}
