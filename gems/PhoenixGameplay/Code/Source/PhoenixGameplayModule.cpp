#include <Phoenix/Gameplay/PhoenixGameplaySystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixGameplayModule final
        : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixGameplayModule, "{C993DED1-FC09-4411-9436-04D101E95908}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixGameplayModule, AZ::SystemAllocator);

        PhoenixGameplayModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixGameplaySystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixGameplaySystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixGameplayModule, Phoenix::PhoenixGameplayModule)
}
