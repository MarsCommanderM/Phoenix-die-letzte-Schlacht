#include <AzCore/Component/Component.h>

namespace Phoenix
{
    class PhoenixGameplaySystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixGameplaySystemComponent, "{00000000-0000-0000-0000-bd3ba04db38c}");
        void Activate() override {}
        void Deactivate() override {}
    };
}
