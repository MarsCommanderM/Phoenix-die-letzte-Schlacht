#pragma once

#include <AzCore/Component/Component.h>

namespace Phoenix
{
    //! Gem-level system component for PhoenixTools.
    //!
    //! Declared in a header so that PhoenixToolsModule can register its
    //! descriptor; a component whose type is only visible inside its own
    //! translation unit can never be reflected or created.
    class PhoenixToolsSystemComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixToolsSystemComponent, "{C9A221DE-79A3-4D32-A67B-760C984B424A}");

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);

    protected:
        void Activate() override;
        void Deactivate() override;
    };
}
