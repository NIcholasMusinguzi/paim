import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../client";
import type { components } from "../schema";

export type Post = components["schemas"]["Post"];
type PostCreateBody = components["schemas"]["PostCreate"];
export type Comment = components["schemas"]["Comment"];

export function usePosts() {
  return useQuery({
    queryKey: ["posts"] as const,
    queryFn: () => api<Post[]>("/posts/"),
  });
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PostCreateBody) => api<Post>("/posts/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });
}

export function useComments(postId: number | null) {
  return useQuery({
    queryKey: ["posts", postId, "comments"] as const,
    queryFn: () => api<Comment[]>(`/posts/${postId}/comments/`),
    enabled: postId != null,
  });
}

export function useAddComment(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      api<Comment>(`/posts/${postId}/comments/`, { method: "POST", body: JSON.stringify({ body }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["posts", postId, "comments"] });
      qc.invalidateQueries({ queryKey: ["posts"] }); // refresh comment_count
    },
  });
}
