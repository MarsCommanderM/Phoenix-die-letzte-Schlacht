#include <Phoenix/Core/PhoenixCoreSystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixCoreModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixCoreModule, "{EAB691C9-1688-49B9-8E50-49E116964002}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixCoreModule, AZ::SystemAllocator);

        PhoenixCoreModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixCoreSystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixCoreSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixCoreModule, Phoenix::PhoenixCoreModule)
} // namespace Phoenix
