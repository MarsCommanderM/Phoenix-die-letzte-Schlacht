#include <AzCore/Module/Module.h>
#include <AzCore/Module/ModuleManagerBus.h>

namespace Phoenix
{
    class PhoenixModule final
        : public AZ::Module
    {
    public:
        AZ_RTTI(PhoenixModule, "{B8E2E0A8-0E9B-4A2E-9D41-7A0E7C8F0001}", AZ::Module);
        AZ_CLASS_ALLOCATOR(PhoenixModule, AZ::SystemAllocator);

        PhoenixModule()
        {
            m_descriptors = AZ::Module::ComponentDescriptors{};
        }
    };

    AZ_DECLARE_MODULE_CLASS(PhoenixModule, Phoenix::PhoenixModule)
}
