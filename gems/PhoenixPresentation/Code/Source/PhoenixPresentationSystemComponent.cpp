#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixPresentationSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixPresentationSystemComponent, "{00000000-0000-0000-0000-37adc51593d7}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
