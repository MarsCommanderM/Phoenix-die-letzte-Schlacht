#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixCoreSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixCoreSystemComponent, "{00000000-0000-0000-0000-b66c04936d4a}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
