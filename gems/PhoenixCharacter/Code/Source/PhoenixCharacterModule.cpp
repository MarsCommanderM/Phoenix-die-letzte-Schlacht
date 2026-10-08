#include <Phoenix/Character/PhoenixCharacterSystemComponent.h>
#include <Phoenix/Character/PhoenixMovementComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixCharacterModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixCharacterModule, "{73892EFC-F73D-4170-8B0F-46798A786162}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixCharacterModule, AZ::SystemAllocator);

        PhoenixCharacterModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixCharacterSystemComponent::CreateDescriptor(),
                    PhoenixMovementComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixCharacterSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixCharacterModule, Phoenix::PhoenixCharacterModule)
} // namespace Phoenix
