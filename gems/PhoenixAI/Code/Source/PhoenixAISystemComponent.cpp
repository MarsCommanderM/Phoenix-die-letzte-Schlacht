#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixAISystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixAISystemComponent, "{00000000-0000-0000-0000-93d172356d66}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
