#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixCharacterSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixCharacterSystemComponent, "{00000000-0000-0000-0000-6b938d10c119}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
