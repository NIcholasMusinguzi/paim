import { useAuth } from "../../app/AuthProvider";
import { PostsSection } from "../farmer/PostsSection";
import { PostComposer } from "../officer/PostComposer";

const CAN_POST = new Set([
  "agent",
  "parish_chief",
  "subcounty_officer",
  "district_officer",
  "national_admin",
]);

function PostsRoute() {
  const { me } = useAuth();
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      {me && CAN_POST.has(me.role) && <PostComposer />}
      <PostsSection />
    </div>
  );
}

export const Component = PostsRoute;
