#include <Phoenix/World/PhoenixWorldSystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixWorldModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixWorldModule, "{577402E2-E66B-4D72-90CA-33021A592877}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixWorldModule, AZ::SystemAllocator);

        PhoenixWorldModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixWorldSystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixWorldSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixWorldModule, Phoenix::PhoenixWorldModule)
} // namespace Phoenix
