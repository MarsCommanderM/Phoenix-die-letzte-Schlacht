#include <Phoenix/Networking/PhoenixNetworkingSystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixNetworkingModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixNetworkingModule, "{E5415A2A-B2F7-40E5-A01B-C746A00A6C9B}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixNetworkingModule, AZ::SystemAllocator);

        PhoenixNetworkingModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixNetworkingSystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixNetworkingSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixNetworkingModule, Phoenix::PhoenixNetworkingModule)
} // namespace Phoenix
