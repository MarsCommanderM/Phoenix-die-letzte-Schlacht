#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixToolsSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixToolsSystemComponent, "{00000000-0000-0000-0000-28c5b6c06c5f}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
