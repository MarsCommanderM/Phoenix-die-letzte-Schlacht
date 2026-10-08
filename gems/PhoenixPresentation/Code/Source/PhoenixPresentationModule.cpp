#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixPresentationModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixPresentationModule, "{00000000-0000-0000-0000-37adc51593d6}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixPresentationModule, AZ::SystemAllocator);
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixPresentationModule, Phoenix::PhoenixPresentationModule)
}
