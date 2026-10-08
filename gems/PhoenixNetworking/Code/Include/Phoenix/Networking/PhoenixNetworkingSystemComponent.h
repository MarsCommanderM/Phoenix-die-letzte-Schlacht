#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixNetworking.
    //!
    //! Declared in a header so that PhoenixNetworkingModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixNetworkingSystemComponent final : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixNetworkingSystemComponent, "{454C67C9-3173-4842-A4F6-F3BBF7B39FBC}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
} // namespace Phoenix
