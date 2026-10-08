#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixAI.
    //!
    //! Declared in a header so that PhoenixAIModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixAISystemComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixAISystemComponent, "{8F31597D-1DB0-4CE8-9DE5-361B68569F73}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
}
