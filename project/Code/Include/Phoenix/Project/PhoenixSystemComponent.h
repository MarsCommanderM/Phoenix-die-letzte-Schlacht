#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Project-level system component.
    //!
    //! Provides PhoenixService, which gem system components may depend on to
    //! order their activation relative to project startup.
    class PhoenixSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixSystemComponent, "{D3D9B1B0-5C32-4B2D-9B1A-7E5B4C9D0002}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
