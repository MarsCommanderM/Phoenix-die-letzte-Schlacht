#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixCharacter.
    //!
    //! Declared in a header so that PhoenixCharacterModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixCharacterSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixCharacterSystemComponent, "{C842C706-6E03-4DEB-8A38-283824855B0C}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
