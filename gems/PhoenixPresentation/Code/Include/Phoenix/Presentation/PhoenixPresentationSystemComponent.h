#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixPresentation.
    //!
    //! Declared in a header so that PhoenixPresentationModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixPresentationSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixPresentationSystemComponent, "{777002A3-0EAE-477D-9675-7B0B2A3C8B39}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
