#include <AzCore/Component/Component.h>
#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    class PhoenixSystemComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(PhoenixSystemComponent, "{D3D9B1B0-5C32-4B2D-9B1A-7E5B4C9D0002}");

        static void Reflect(AZ::ReflectContext* context)
        {
            if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
            {
                serializeContext->Class<PhoenixSystemComponent, AZ::Component>();
            }
        }

        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
        {
            provided.push_back(AZ_CRC_CE("PhoenixService"));
        }

        void Activate() override {}
        void Deactivate() override {}
    };
}
