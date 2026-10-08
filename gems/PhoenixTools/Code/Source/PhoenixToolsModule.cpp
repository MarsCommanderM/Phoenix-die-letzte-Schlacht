#include <Phoenix/Tools/PhoenixToolsSystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixToolsModule final
        : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixToolsModule, "{B0415E7A-A026-4ADD-97F4-9192CCEA439E}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixToolsModule, AZ::SystemAllocator);

        PhoenixToolsModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixToolsSystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixToolsSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixToolsModule, Phoenix::PhoenixToolsModule)
}
