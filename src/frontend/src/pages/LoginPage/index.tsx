import * as Form from "@radix-ui/react-form";
import { useQueryClient } from "@tanstack/react-query";
import { useContext, useState } from "react";
import ContentLogo from "@/assets/Content.svg?react";
import DotsPattern from "@/assets/Background_pattern_decorative.svg?react";
import { SparklesCore } from "@/components/ui/sparkles";
import { useLoginUser } from "@/controllers/API/queries/auth";
import { CustomLink } from "@/customization/components/custom-link";
import { useSanitizeRedirectUrl } from "@/hooks/use-sanitize-redirect-url";
import InputComponent from "../../components/core/parameterRenderComponent/components/inputComponent";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Checkbox } from "../../components/ui/checkbox";
import { SIGNIN_ERROR_ALERT } from "../../constants/alerts_constants";
import { CONTROL_LOGIN_STATE, IS_AUTO_LOGIN } from "../../constants/constants";
import { AuthContext } from "../../contexts/authContext";
import useAlertStore from "../../stores/alertStore";
import type { LoginType } from "../../types/api";
import type {
  inputHandlerEventType,
  loginInputStateType,
} from "../../types/components";

export default function LoginPage(): JSX.Element {
  const [inputState, setInputState] =
    useState<loginInputStateType>(CONTROL_LOGIN_STATE);
  const [rememberMe, setRememberMe] = useState(false);

  const { password, username } = inputState;

  useSanitizeRedirectUrl();

  const { login, clearAuthSession } = useContext(AuthContext);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  function handleInput({
    target: { name, value },
  }: inputHandlerEventType): void {
    setInputState((prev) => ({ ...prev, [name]: value }));
  }

  const { mutate } = useLoginUser();
  const queryClient = useQueryClient();

  function signIn() {
    const user: LoginType = {
      username: username.trim(),
      password: password.trim(),
    };

    mutate(user, {
      onSuccess: (data) => {
        clearAuthSession();
        login(data.access_token, "login", data.refresh_token);
        queryClient.clear();
      },
      onError: (error) => {
        setErrorData({
          title: SIGNIN_ERROR_ALERT,
          list: [error["response"]["data"]["detail"]],
        });
      },
    });
  }

  function handleGoogleSignIn() {
    // TODO: Implement Google Sign In
    console.log("Google Sign In clicked");
  }

  return (
    <Form.Root
      onSubmit={(event) => {
        console.log("password -->", password);
        if (password === "") {
          event.preventDefault();
          return;
        }
        signIn();
        const _data = Object.fromEntries(new FormData(event.currentTarget));
        event.preventDefault();
      }}
      className="relative h-screen w-full overflow-hidden"
    >
      {/* Background with dots pattern */}
      <div className="absolute inset-0 bg-white">
        <DotsPattern className="absolute left-1/2 top-[-264px] h-[768px] w-[768px] -translate-x-1/2 opacity-100" />
      </div>

      {/* Main content */}
      <div className="relative z-10 flex h-full w-full flex-col items-center justify-center">
        <div className="flex w-full max-w-[468px] flex-col items-center justify-center gap-6 px-6">
          {/* Logo */}
          <div className="flex flex-col items-center gap-6">
            <ContentLogo className="h-[60px] w-[60px]" />

            {/* Title and subtitle */}
            <div className="flex flex-col items-center gap-3">
              <h1 className="text-[30px] font-semibold leading-[38px] text-[#101828]">
                Log in to your account
              </h1>
              <p className="text-center text-base font-normal leading-6 text-[#475467]">
                Access everything you need to learn, teach, and automate your academic workflow.
              </p>
            </div>
          </div>

          {/* Form fields */}
          <div className="flex w-full flex-col gap-5">
            {/* Email field */}
            <div className="w-full">
              <Form.Field name="username">
                <Form.Label className="mb-1.5 block text-sm font-medium leading-5 text-[#344054]">
                  Email
                </Form.Label>

                <Form.Control asChild>
                  <Input
                    type="text"
                    onChange={({ target: { value } }) => {
                      handleInput({ target: { name: "username", value } });
                    }}
                    value={username}
                    className="h-11 w-full rounded-lg border border-[#D0D5DD] bg-white px-3.5 py-2.5 text-base text-[#101828] placeholder:text-[#667085] focus:border-[#3559E0] focus:ring-1 focus:ring-[#3559E0]"
                    required
                    placeholder="Enter your email"
                  />
                </Form.Control>

                <Form.Message match="valueMissing" className="mt-1.5 text-sm text-destructive">
                  Please enter your email
                </Form.Message>
              </Form.Field>
            </div>

            {/* Password field */}
            <div className="w-full">
              <Form.Field name="password">
                <Form.Label className="mb-1.5 block text-sm font-medium leading-5 text-[#344054]">
                  Password
                </Form.Label>

                <InputComponent
                  onChange={(value) => {
                    handleInput({ target: { name: "password", value } });
                  }}
                  value={password}
                  isForm
                  password={true}
                  required
                  placeholder="••••••••"
                  className="h-11 w-full rounded-lg border border-[#D0D5DD] bg-white px-3.5 py-2.5 text-base text-[#101828] placeholder:text-[#667085] focus:border-[#3559E0] focus:ring-1 focus:ring-[#3559E0]"
                />

                <Form.Message className="mt-1.5 text-sm text-destructive" match="valueMissing">
                  Please enter your password
                </Form.Message>
              </Form.Field>
            </div>

            {/* Remember me and Forgot password */}
            {/* <div className="flex w-full items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                  className="h-4 w-4 rounded border-[#D0D5DD]"
                />
                <label
                  htmlFor="remember"
                  className="text-sm font-medium leading-5 text-[#344054] cursor-pointer"
                >
                  Remember for 30 days
                </label>
              </div>
              <CustomLink to="/forgot-password" className="text-sm font-semibold leading-5 text-[#3559E0] hover:text-[#2347C5]">
                Forgot password
              </CustomLink>
            </div> */}

            {/* Sign in button */}
            <Form.Submit asChild>
              <Button
                className="h-11 w-full rounded-lg bg-[#0969DA] text-base font-semibold text-white hover:bg-[#0156AA] focus:ring-4 focus:ring-[#D4DCFC] box-shadow-[0 1px 2px 0 rgba(16, 24, 40, 0.05)]"
                type="submit"
              >
                Sign in
              </Button>
            </Form.Submit>

            {/* Sign in with Google */}
            {/* <Button
              type="button"
              variant="outline"
              onClick={handleGoogleSignIn}
              className="h-11 w-full rounded-lg border border-[#D0D5DD] bg-white text-base font-semibold text-[#344054] hover:bg-[#F9FAFB] focus:ring-4 focus:ring-[#F2F4F7]"
            >
              <svg className="mr-3 h-5 w-5" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.9895 10.1871C19.9895 9.36767 19.9214 8.76973 19.7742 8.14966H10.1992V11.848H15.8195C15.7062 12.7671 15.0943 14.1512 13.7346 15.0813L13.7155 15.2051L16.7429 17.4969L16.9527 17.5174C18.879 15.7789 19.9895 13.221 19.9895 10.1871Z" fill="#4285F4"/>
                <path d="M10.1993 19.9313C12.9527 19.9313 15.2643 19.0454 16.9527 17.5174L13.7346 15.0813C12.8734 15.6682 11.7176 16.0779 10.1993 16.0779C7.50242 16.0779 5.21352 14.3395 4.39759 11.9366L4.27799 11.9465L1.13003 14.3273L1.08887 14.4391C2.76588 17.6945 6.21061 19.9313 10.1993 19.9313Z" fill="#34A853"/>
                <path d="M4.39748 11.9366C4.18219 11.3166 4.05759 10.6521 4.05759 9.96565C4.05759 9.27909 4.18219 8.61473 4.38615 7.99466L4.38045 7.8626L1.19304 5.44366L1.08875 5.49214C0.397576 6.84305 0.000976562 8.36008 0.000976562 9.96565C0.000976562 11.5712 0.397576 13.0882 1.08875 14.4391L4.39748 11.9366Z" fill="#FBBC05"/>
                <path d="M10.1993 3.85336C12.1142 3.85336 13.406 4.66168 14.1425 5.33717L17.0207 2.59107C15.253 0.985496 12.9527 0 10.1993 0C6.2106 0 2.76588 2.23672 1.08887 5.49214L4.38626 7.99466C5.21352 5.59183 7.50242 3.85336 10.1993 3.85336Z" fill="#EB4335"/>
              </svg>
              Sign in with Google
            </Button> */}

            {/* Sign up link */}
            <div className="text-center">
              {/* <span className="text-sm font-normal text-[#475467]">
                Don't have an account?{" "}
                <CustomLink to="/signup" className="font-semibold text-[#3559E0] hover:text-[#2347C5]">
                  Sign up
                </CustomLink>
              </span> */}
            </div>
          </div>
        </div>
      </div>
    </Form.Root>
  );
}
