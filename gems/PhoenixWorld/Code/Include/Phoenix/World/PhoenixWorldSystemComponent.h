#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixWorld.
    //!
    //! Declared in a header so that PhoenixWorldModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixWorldSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixWorldSystemComponent, "{2DBF37B6-B548-4BBF-961F-767A2341B75B}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
