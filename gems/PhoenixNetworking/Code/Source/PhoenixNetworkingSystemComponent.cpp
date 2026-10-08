#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixNetworkingSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixNetworkingSystemComponent, "{00000000-0000-0000-0000-f73663da9105}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
