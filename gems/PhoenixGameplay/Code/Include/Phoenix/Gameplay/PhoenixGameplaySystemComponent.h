#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixGameplay.
    //!
    //! Declared in a header so that PhoenixGameplayModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixGameplaySystemComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixGameplaySystemComponent, "{DF41F8AC-F00B-41B3-9594-7B7838B83CE4}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
}
