#include <Phoenix/Presentation/PhoenixPresentationSystemComponent.h>

#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

namespace Phoenix
{
    class PhoenixPresentationModule final : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixPresentationModule, "{D8620ED0-B11B-43A6-9A79-BD108D772AC4}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixPresentationModule, AZ::SystemAllocator);

        PhoenixPresentationModule()
        {
            m_descriptors.insert(
                m_descriptors.end(),
                {
                    PhoenixPresentationSystemComponent::CreateDescriptor(),
                });
        }

        //! Without this the system component is reflected but never created.
        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<PhoenixPresentationSystemComponent>(),
            };
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixPresentationModule, Phoenix::PhoenixPresentationModule)
} // namespace Phoenix
