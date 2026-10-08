#pragma once
namespace Phoenix
{
    struct ValidationResult
    {
        unsigned errors = 0;
        unsigned warnings = 0;
        bool IsValid() const { return errors == 0; }
    };
}
