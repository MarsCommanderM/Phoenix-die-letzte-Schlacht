#pragma once
#include <AzCore/std/string/string.h>

namespace Phoenix
{
    enum class ResultCode
    {
        Success,
        Failure,
        InvalidState,
        NotFound,
        Unavailable,
        Rejected,
        Timeout,
        Unsupported
    };

    struct Result
    {
        ResultCode code = ResultCode::Success;
        AZStd::string message;

        explicit operator bool() const
        {
            return code == ResultCode::Success;
        }
    };
}
