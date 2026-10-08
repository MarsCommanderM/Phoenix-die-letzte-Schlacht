#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixWorldSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixWorldSystemComponent, "{00000000-0000-0000-0000-c86be7e7aac8}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
