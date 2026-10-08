#include <Phoenix/AI/PhoenixAISystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixAIModule final
        : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixAIModule, "{C16BE97C-3DEB-4849-9B0D-65AE11A289AD}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixAIModule, AZ::SystemAllocator);

        PhoenixAIModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixAISystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixAISystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixAIModule, Phoenix::PhoenixAIModule)
}
