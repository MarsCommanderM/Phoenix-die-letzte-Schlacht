#include <Phoenix/Tools/PhoenixToolsSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixToolsSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixToolsSystemComponent, AZ::Component>()->Version(1);
        }
    }

    void PhoenixToolsSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixToolsService"));
    }

    void PhoenixToolsSystemComponent::Activate()
    {
    }

    void PhoenixToolsSystemComponent::Deactivate()
    {
    }
} // namespace Phoenix
