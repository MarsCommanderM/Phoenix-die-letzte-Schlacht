#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixCore.
    //!
    //! Declared in a header so that PhoenixCoreModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixCoreSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixCoreSystemComponent, "{33B3C464-5D78-44BB-95E0-4BD2A968399B}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
